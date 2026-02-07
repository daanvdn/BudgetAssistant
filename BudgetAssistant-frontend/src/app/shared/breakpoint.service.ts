import { Injectable, signal, DestroyRef, inject } from '@angular/core';
import { BreakpointObserver } from '@angular/cdk/layout';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';

/** Breakpoint matching the local $breakpoint-mobile: 768px used in component SCSS files */
const MOBILE_BREAKPOINT = '(max-width: 768px)';

@Injectable({ providedIn: 'root' })
export class BreakpointService {
  private readonly destroyRef = inject(DestroyRef);
  private readonly breakpointObserver = inject(BreakpointObserver);

  /** true when viewport width ≤ 768px */
  readonly isMobile = signal(false);

  constructor() {
    this.breakpointObserver
      .observe(MOBILE_BREAKPOINT)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe(result => this.isMobile.set(result.matches));
  }
}
