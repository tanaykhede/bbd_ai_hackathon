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
        const assistantMessage = { role: 'assistant', content: response.response };
        this.messages.push(assistantMessage);
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
