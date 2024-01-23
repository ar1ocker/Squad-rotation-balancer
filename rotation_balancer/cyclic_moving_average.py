def cyclic_moving_average(list_values, window):
    """
    Расчет скользящего среднего на буфере, принимая буфер за циклический
    """
    len_list_values = len(list_values)

    assert len_list_values > window

    ret_list = [None] * len_list_values

    _sum = 0

    # Суммирование конца буфера
    for i in range(len_list_values - window + 1, len_list_values):
        _sum += list_values[i]

    for i in range(len_list_values):
        _sum += list_values[i]
        ret_list[i] = _sum / window
        _sum -= list_values[i - window + 1]

    return ret_list
