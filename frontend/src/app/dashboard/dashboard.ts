import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ClassifyCase } from '../classify-case/classify-case';

@Component({
  selector: 'app-dashboard',
  imports: [CommonModule, ClassifyCase],
  templateUrl: './dashboard.html',
  styleUrl: './dashboard.css'
})
export class Dashboard {
  selectedTab = 'classify';

  selectTab(tab: string) {
    this.selectedTab = tab;
  }
}
