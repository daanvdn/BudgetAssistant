import { Meta, StoryObj, applicationConfig } from '@storybook/angular';
import { moduleMetadata } from '@storybook/angular';
import { NavigationComponent } from './navigation.component';
import { MatSidenavModule } from '@angular/material/sidenav';
import { MatListModule } from '@angular/material/list';
import { MatButtonModule } from '@angular/material/button';
import { RouterLink, RouterLinkActive, RouterOutlet, ActivatedRoute, Router, RouterModule, provideRouter } from '@angular/router';
import { FontAwesomeModule } from '@fortawesome/angular-fontawesome';
import { AuthService } from '../auth/auth.service';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { importProvidersFrom } from '@angular/core';
import { action } from '@storybook/addon-actions';
import { of } from 'rxjs';
// Mock AuthService
const mockAuthService = {
  logout: action('logout clicked')
};

// Mock ActivatedRoute
const mockActivatedRoute = {
  params: of({}),
  queryParams: of({}),
  fragment: of(''),
  data: of({}),
  snapshot: {
    params: {},
    queryParams: {},
    fragment: '',
    data: {}
  }
};

// Mock Router
const mockRouter = {
  navigate: action('navigate'),
  navigateByUrl: action('navigateByUrl'),
  events: of({}),
  url: ''
};

/**
 * Storybook stories for the NavigationComponent
 * 
 * These stories demonstrate the navigation sidebar component in different states:
 * - Default: Shows the navigation component in its default collapsed state
 * - HoverTransition: Demonstrates the transition between the default state and hover state
 *   where the sidebar expands and text labels appear
 */
const meta: Meta<NavigationComponent> = {
  title: 'Components/Navigation',
  component: NavigationComponent,
  decorators: [
    moduleMetadata({
      imports: [
        MatSidenavModule,
        MatListModule,
        MatButtonModule,
        FontAwesomeModule,
        RouterModule
      ],
      providers: [
        { provide: AuthService, useValue: mockAuthService },
        { provide: ActivatedRoute, useValue: mockActivatedRoute },
        { provide: Router, useValue: mockRouter }
      ],
    }),
    applicationConfig({
      providers: [
        importProvidersFrom(BrowserAnimationsModule),
        provideRouter([])
      ],
    }),
  ],
  parameters: {
    layout: 'fullscreen',
  },
};



export default meta;
type Story = StoryObj<NavigationComponent>;

/**
 * Default state story
 * 
 * This story shows the navigation component in its default state with a collapsed sidebar.
 * In this state, only the icons are visible, and the text labels are hidden.
 */
export const Default: Story = {
  args: {},
  parameters: {
    docs: {
      description: {
        story: 'The navigation sidebar in its default collapsed state. Only icons are visible.'
      }
    }
  },
  decorators: [
    applicationConfig({
      providers: []
    }),
    moduleMetadata({
      imports: []
    })
  ],
  render: (args) => ({
    props: args,
    styles: [`
      :host {
        display: block;
        height: 100vh;
      }
      mat-drawer-container {
        height: 100%;
      }
    `],
    template: `
      <div style="height: 100vh; display: flex;">
        <app-navigation></app-navigation>
      </div>
    `,
  })
};
