import numpy as np

from .arguments import execute, parser
from .io import files_in, save_netcdf
from .plotting import plot_map
from .processing import monthly_anomaly


def run(args):
    field = monthly_anomaly(files_in(args.input, ".nc"), args.climatology, args.variable)
    if args.netcdf:
        save_netcdf(field, args.netcdf)
    plot_map(
        field.values,
        field.lat,
        field.lon,
        args.output,
        title=args.title or f"Anomalia média {args.variable}",
        label="Anomalia (°C)",
        levels=np.arange(-3, 3.5, 0.5),
        cmap="coolwarm",
        shapefile=args.shapefile,
        states=["PR", "SC", "RS"] if args.region == "sul" else None,
        extent=[-57.6, -48, -33.75, -22.5] if args.region == "sul" else [-75, -34, -35, 7],
    )


def main(argv=None):
    p = parser("Anomalia mensal SAMET; use arquivos do mesmo mês e unidade da climatologia")
    p.add_argument("--input", required=True, help="Diretório de arquivos diários NetCDF")
    p.add_argument("--climatology", required=True)
    p.add_argument("--variable", choices=["tmin", "tmax"], default="tmin")
    p.add_argument("--region", choices=["brasil", "sul"], default="brasil")
    p.add_argument("--netcdf", help="Salvar também o campo calculado")
    execute(p, run, argv)
