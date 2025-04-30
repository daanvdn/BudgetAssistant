import { Injectable } from '@angular/core';

@Injectable({
  providedIn: 'root'
})
export class DateUtilsService {
  constructor() { }

  /**
   * Parses a date string in the format dd/MM/yyyy into a Date object
   * @param dateStr The date string to parse
   * @returns A Date object or null if the string is invalid or undefined
   */
  parseDate(dateStr: string | undefined | null): Date | null {
    if (dateStr === undefined || dateStr === null) {
      return null;
    }

    // Parse date in format dd/MM/yyyy
    const parts = dateStr.split('/');
    if (parts.length === 3) {
      const day = parseInt(parts[0], 10);
      const month = parseInt(parts[1], 10) - 1; // Months are 0-based in JS Date
      const year = parseInt(parts[2], 10);
      return new Date(year, month, day);
    }

    return null;
  }
}