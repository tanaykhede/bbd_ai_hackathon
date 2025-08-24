import { Routes } from '@angular/router';
import { Login } from './login/login';
import { ChatComponent } from './chat/chat';

export const routes: Routes = [
    { path: 'login', component: Login },
    { path: 'chat', component: ChatComponent },
    { path: 'dashboard', redirectTo: '/chat', pathMatch: 'full' },
    { path: '', redirectTo: '/login', pathMatch: 'full' }
];
