import { Logger } from "@nestjs/common";

export class CircuitBreaker {
  private readonly logger = new Logger(CircuitBreaker.name);
  private failureCount = 0;
  private state: "CLOSED" | "OPEN" | "HALF_OPEN" = "CLOSED";
  private nextAttemptTime = Date.now();

  constructor(
    private readonly serviceName: string,
    private readonly threshold: number = 5,
    private readonly timeout: number = 60000
  ) {}

  async execute<T>(fn: () => Promise<T>): Promise<T> {
    if (this.state === "OPEN") {
      if (Date.now() < this.nextAttemptTime) {
        throw new Error(`Circuit breaker is OPEN for ${this.serviceName}`);
      }
      this.state = "HALF_OPEN";
    }

    try {
      const result = await fn();
      this.onSuccess();
      return result;
    } catch (error) {
      this.onFailure();
      throw error;
    }
  }

  private onSuccess(): void {
    this.failureCount = 0;
    this.state = "CLOSED";
  }

  private onFailure(): void {
    this.failureCount++;

    if (this.failureCount >= this.threshold) {
      this.state = "OPEN";
      this.nextAttemptTime = Date.now() + this.timeout;
      this.logger.error(`${this.serviceName}: Circuit breaker OPEN`);
    }
  }

  getState(): string {
    return this.state;
  }

  getFailureCount(): number {
    return this.failureCount;
  }
}
