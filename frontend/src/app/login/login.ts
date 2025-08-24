import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';

@Component({
  selector: 'app-login',
  imports: [FormsModule],
  templateUrl: './login.html',
  styleUrl: './login.css'
})
export class Login {
  username = '';
  password = '';

  constructor(private router: Router) {}

  login() {
    // Handle login logic here
    console.log('Username:', this.username);
    console.log('Password:', this.password);
  this.router.navigate(['/chat']);
  }
}
