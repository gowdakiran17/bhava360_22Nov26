// Later adapters implement these server-only contracts.
export interface PaymentPort {
  createCheckout(orderId: string): Promise<{ available: boolean }>;
}

export interface OtpPort {
  sendChallenge(challengeId: string): Promise<{ available: boolean }>;
}

export interface EmailPort {
  sendMessage(messageId: string): Promise<{ available: boolean }>;
}

export const offlineProviders: PaymentPort & OtpPort & EmailPort = {
  async createCheckout() { return { available: false }; },
  async sendChallenge() { return { available: false }; },
  async sendMessage() { return { available: false }; }
};
