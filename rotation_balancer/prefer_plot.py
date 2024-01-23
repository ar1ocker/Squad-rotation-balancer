import asyncio
import csv
import io

import matplotlib.pyplot as plt
import nicegui
from matplotlib import ticker
from nicegui import run, ui

from cyclic_moving_average import cyclic_moving_average


class PreferPlot(nicegui.element.Element):
    def __init__(self):
        super().__init__("div")
        self.last_task_get_svg = None

    async def update_plot(
        self, prefers, rotation, window, calculate_average, custom_average
    ):
        if self.last_task_get_svg:
            self.last_task_get_svg.cancel()

        try:
            parsed_window = self._parse_window(window)
            parsed_prefers = self._parse_prefers(prefers)
        except ValueError as e:
            ui.notify(str(e), type="warning")
            return

        parsed_rotation = self._parse_rotation(rotation)

        if not self._validate_params(
            parsed_prefers,
            parsed_rotation,
            parsed_window,
            calculate_average,
            custom_average,
        ):
            return

        self.last_task_get_svg = asyncio.create_task(
            run.cpu_bound(
                get_chart_svg,
                parsed_prefers,
                parsed_rotation,
                parsed_window,
                calculate_average,
                custom_average,
            )
        )

        new_svg = await self.last_task_get_svg

        if new_svg is not None:
            self._props["innerHTML"] = new_svg
            self.update()
            ui.notify("Расчитали", color="green")

    def _validate_params(
        self, prefers, rotation, window, calculate_average, custom_average
    ) -> bool:
        is_valid = True

        if calculate_average and custom_average is None:
            ui.notify("Задайте среднее значение в настройках")
            is_valid = False

        if window < 1:
            ui.notify("Окно ротации должно быть больше 0")
            is_valid = False

        if len(rotation) == 0:
            ui.notify("Введите ротацию")
            is_valid = False
        elif len(rotation) < window:
            ui.notify("Окно должно быть меньше количества карт в ротации")
            is_valid = False

        for layer in rotation:
            if layer not in prefers:
                ui.notify(f"Карта {layer} не найдена в списке предпочтений")
                is_valid = False

        return is_valid

    def _parse_window(self, window):
        if window is None:
            raise ValueError("Введите окно скользящего среднего")

        try:
            parsed_window = int(window)
        except ValueError:
            raise ValueError("Окно должно быть числом")

        return parsed_window

    def _parse_prefers(self, prefers) -> dict:
        reader = csv.DictReader(
            prefers.split("\n"),
            ("layer", "prefer"),
            delimiter=";",
        )

        prefers_by_map = {}

        for key, row in enumerate(reader):
            layer = row["layer"].strip().lower()

            if row["prefer"] is None:
                raise ValueError(
                    f"В строке '{key + 1}' не найден параметр предпочтения"
                    " игроков"
                )

            try:
                prefer = float(row["prefer"].strip().replace(",", "."))

                if prefer > 10:
                    raise ValueError()

            except ValueError:
                raise ValueError(
                    f"В строке {key + 1} параметр предпочтения игроков должен"
                    " быть числом с плавающей точкой от 0 до 10"
                )

            prefers_by_map[layer] = prefer * 10

        return prefers_by_map

    def _parse_rotation(self, rotation):
        splitted_rotation = rotation.split("\n")

        ret_rotation = []

        for layer in splitted_rotation:
            stripped_layer = layer.strip()
            if stripped_layer and not stripped_layer.startswith("/"):
                # Название карты идёт первым в названии леера
                ret_rotation.append(stripped_layer.split("_")[0].lower())

        return ret_rotation


def get_chart_svg(
    prefers, rotation, window, calculate_average, custom_average
):
    rotation_prefer = [prefers[layer] for layer in rotation]
    prefers_average = cyclic_moving_average(
        rotation_prefer,
        window,
    )

    figure = get_figure(
        rotation,
        rotation_prefer,
        prefers_average,
        custom_average if not calculate_average else None,
    )

    with io.StringIO() as output:
        figure.savefig(output, format="svg")
        return output.getvalue()


def get_figure(rotation, prefers, prefer_average, mid=None):
    if mid is None:
        mid = sum(prefers) / len(prefers)

    x = range(len(prefers))

    fig = plt.figure(layout="tight")
    fig.set_size_inches(11, 6)
    ax = fig.add_subplot()

    # Поворачиваем текст в x на 45 градусов, чтобы он был читаемый
    plt.setp(
        ax.get_xticklabels(),
        rotation=45,
        ha="right",
        rotation_mode="anchor",
    )

    ax.margins(0.02, 0.02)

    # Рисуем
    ax.plot(
        prefer_average,
        ".-",
        label="Скользящее среднее по картам",
    )
    ax.plot(
        prefers,
        ".--",
        alpha=0.4,
        label="Исходный процент игроков",
    )
    ax.axhline(mid, color="orange", label="Среднее значение ротации")

    # Заливаем от мида к нижней границе prefer
    ax.fill_between(
        x,
        mid,
        prefer_average,
        where=[prefer < mid for prefer in prefer_average],
        color="red",
        alpha=0.2,
        interpolate=True,
    )

    # Разное
    ax.legend(loc="upper left", bbox_to_anchor=(1, 1))
    ax.set_ylabel("Процент игроков")
    ax.set_title("Баланс ротации")
    ax.set_xticks(x, rotation)
    ax.yaxis.set_major_formatter(ticker.PercentFormatter())
    ax.yaxis.set_major_locator(ticker.MultipleLocator(5))

    ax.grid()

    return fig
