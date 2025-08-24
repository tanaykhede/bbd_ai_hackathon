import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class ChatService {
  private apiUrl = 'http://localhost:8001/chat'; // URL of your MCP server's chat endpoint

  constructor(private http: HttpClient) { }

  sendMessage(message: string, history: any[]): Observable<any> {
    return this.http.post<any>(this.apiUrl, { message, history });
  }
}
