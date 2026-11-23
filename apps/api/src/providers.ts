// Later adapters implement these server-only contracts.
export interface PaymentPort {
  createCheckout(orderId: string): Promise<{ available: boolean }>;
}

export interface OtpPort {
  send(channel: 'phone' | 'email', recipient: string, code: string): void;
}

export interface EmailPort {
  sendMessage(messageId: string): Promise<{ available: boolean }>;
}

export const offlineProviders: PaymentPort & EmailPort = {
  async createCheckout() {
    return { available: false };
  },
  async sendMessage() {
    return { available: false };
  },
};
