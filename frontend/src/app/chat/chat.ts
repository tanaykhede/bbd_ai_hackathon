import { Component } from '@angular/core';
import { ChatService } from '../chat.service';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

@Component({
  selector: 'app-chat',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './chat.html',
  styleUrls: ['./chat.css']
})
export class ChatComponent {
  messages: { role: string, content: string }[] = [];
  newMessage: string = '';
  isLoading: boolean = false;

  constructor(private chatService: ChatService) { }

  sendMessage() {
    if (this.newMessage.trim() === '') {
      return;
    }

    const userMessage = { role: 'user', content: this.newMessage };
    this.messages.push(userMessage);
    this.isLoading = true;

    // We need to transform our simple message format to the one the API expects
    const historyForApi = this.messages.slice(0, -1).map(msg => ({
      role: msg.role,
      content: msg.content
    }));

    this.chatService.sendMessage(this.newMessage, historyForApi).subscribe({
      next: (response) => {
        // Backend returns { response: string, history: anthropic-shaped messages }
        // We'll append the assistant response. If multiple logical responses are embedded (e.g. split by two consecutive newlines), create separate bubbles.
        const raw = response.response || '';
        const parts = raw
          .split(/\n{2,}/) // split on blank lines
          .map((p: string) => p.trim())
          .filter((p: string) => p.length > 0);

        if (parts.length === 0) {
          this.messages.push({ role: 'assistant', content: raw });
        } else if (parts.length === 1) {
          this.messages.push({ role: 'assistant', content: parts[0] });
        } else {
          parts.forEach((p: string) => this.messages.push({ role: 'assistant', content: p }));
        }

        // Optionally sync full history for future context (keeping only role/text pairs)
        if (Array.isArray(response.history)) {
          // Reconstruct a simplified history from backend if needed (skip due to duplication risk)
        }

        this.isLoading = false;
        this.newMessage = '';
      },
      error: (error) => {
        console.error('Error sending message:', error);
        const errorMessage = { role: 'assistant', content: 'Sorry, something went wrong. Please check the console.' };
        this.messages.push(errorMessage);
        this.isLoading = false;
      }
    });
  }
}
