from nicegui import ui
from prefer_plot import PreferPlot


@ui.page("/")
def index():
    async def update_plot():
        await chart.update_plot(
            prefers.value,
            rotation.value,
            window.value,
            calculate_average.value,
            custom_average.value,
        )

    with ui.tabs().classes("w-full") as tabs:
        preferences_tab = ui.tab("Настройки")
        rotation_tab = ui.tab("Ротация")

    with ui.tab_panels(tabs, value=preferences_tab).classes("w-full"):
        with ui.tab_panel(preferences_tab).on(
            "keydown.enter",
            update_plot,
        ):
            prefers = (
                ui.textarea(
                    "Список предпочтений игроков к картам",
                    placeholder=(
                        "Формат списка: название карты;оценка игроков (число"
                        " от 0 до 10)"
                    ),
                )
                .classes("w-full")
                .props("autogrow")
            )

            window = ui.number(
                "Окно расчета скользящего среднего",
                value=3,
                precision=0,
                format="%d",
                min=0,
            ).classes("w-full")

            calculate_average = (
                ui.checkbox(
                    "Расчитывать ли автоматически среднее предпочтение между"
                    " картами в ротации"
                )
                .classes("w-full")
                .on(
                    "click",
                    update_plot,
                )
            )

            custom_average = (
                ui.number(
                    "Среднее значение предпочтения игроков для ротации",
                    value=70,
                    precision=0,
                    format="%d",
                    min=0,
                    max=100,
                )
                .bind_visibility_from(calculate_average, "value", value=False)
                .classes("w-full")
            )
        with ui.tab_panel(rotation_tab):
            rotation = (
                ui.textarea(label="Список карт в ротации")
                .classes("w-full")
                .on("keydown.enter", update_plot)
            )
            chart = PreferPlot()
            ui.button(
                "Обновить график",
                on_click=update_plot,
            )


ui.run(
    host="0.0.0.0",
    port=8000,
    title="Балансировщик ротаций",
    favicon="📊",
    show=False,
    reload=False,
)
