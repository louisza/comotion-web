declare module "leaflet.heat" {
  import * as L from "leaflet";
  namespace L {
    function heatLayer(
      latlngs: [number, number, number?][],
      options?: {
        radius?: number;
        blur?: number;
        maxZoom?: number;
        max?: number;
        gradient?: Record<number, string>;
      }
    ): any;
  }
  export = L;
}
