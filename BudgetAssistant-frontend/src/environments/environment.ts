// This file can be replaced during build by using the `fileReplacements` array.
// `ng build` replaces `environment.ts` with `environment.prod.ts`.
// The list of file replacements can be found in `angular.json`.

export const environment = {
  production: false,
  //backendUrl: "http://localhost:8080",
  API_BASE_PATH: 'http://localhost:8080',
  // DEV_AUTH_BYPASS: Header name to add for dev auth bypass. Must match backend's DEV_BYPASS_HEADER setting.
  devBypassHeader: 'X-DEV-AUTH'
};

/*
 * For easier debugging in development mode, you can import the following file
 * to ignore zone related error stack frames such as `zone.run`, `zoneDelegate.invokeTask`.
 *
 * This import should be commented out in production mode because it will have a negative impact
 * on performance if an error is thrown.
 */
// import 'zone.js/plugins/zone-error';  // Included with Angular CLI.
