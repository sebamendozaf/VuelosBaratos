import sys
from datetime import datetime
import google_flights
import flight_api
import price_tracker
import telegram_bot
import telegram_commands
import config


def run():
    print(f"[{datetime.now().isoformat()}] Iniciando búsqueda desde {config.ORIGIN_AIRPORT}...")

    # Revisar si el usuario mandó algún comando por Telegram
    telegram_commands.process_commands()
    selected_month = telegram_commands.get_selected_month()
    if selected_month:
        month_name = [k for k, v in config.MESES.items() if v == selected_month]
        print(f"Mes seleccionado: {month_name[0].capitalize() if month_name else selected_month}")

    # Buscar vuelos
    all_offers = google_flights.search_all_destinations(selected_month)
    all_offers.extend(flight_api.search_all_destinations())
    print(f"Total: {len(all_offers)} ofertas encontradas")

    if not all_offers:
        print("No se encontraron vuelos.")
        return

    # Guardar historial completo
    price_tracker.record_prices(all_offers)

    # Quedarse solo con el vuelo más barato por destino
    cheapest_by_dest = {}
    for offer in all_offers:
        dest = offer["destination"]
        if dest not in cheapest_by_dest or offer["price"] < cheapest_by_dest[dest]["price"]:
            cheapest_by_dest[dest] = offer
    best_offers = list(cheapest_by_dest.values())
    print(f"Mejor precio por destino: {len(best_offers)} vuelos")

    # Detectar ofertas y filtrar duplicadas
    deals = price_tracker.find_deals(best_offers)
    new_deals = [d for d in deals if not price_tracker.is_already_notified(d)]
    print(f"Ofertas nuevas: {len(new_deals)}")

    for deal in new_deals:
        city = deal.get("city", deal["destination"])
        print(f"  -> {deal['origin']} -> {city}: USD {deal['price']:,.0f} [{deal.get('deal_type', '')}]")
        if telegram_bot.notify_deal(deal):
            price_tracker.mark_as_notified(deal)

    print(f"[{datetime.now().isoformat()}] Búsqueda finalizada.")


if __name__ == "__main__":
    run()
