import { Component } from '@angular/core';
import { Router } from '@angular/router';
import { CommonModule } from '@angular/common';
import { ChatComponent } from '../chat/chat';

@Component({
  selector: 'app-dashboard',
  imports: [CommonModule, ChatComponent],
  templateUrl: './dashboard.html',
  styleUrl: './dashboard.css'
})
export class Dashboard {
  constructor(private router: Router) {}

  logout() {
    // Clear any stored auth (placeholder if added later)
    try {
      localStorage.removeItem('authToken');
    } catch {}
    this.router.navigate(['/login']);
  }
}
