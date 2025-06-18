def get_frames_from_frame_range(
        range_str: str, anim_start: int, anim_end: int
) -> list[int]:
    """
    Generates a list of frame numbers from a single slice string like "1:10" or
    "1:2:10". This is based on Julia's slicing syntax.

    :param range_str: The string defining a single frame slice.
    :param anim_start: The starting frame of the animation.
    :param anim_end: The ending frame of the animation.
    :return: A list of frame numbers.
    """
    frames: list[int] = []
    if range_str == "":
        return []

    # Get the parts of the range string
    parts = range_str.split(':')
    start_str, step_str, end_str = '', '1', ''
    if len(parts) == 1:
        # A single number
        start_str = end_str = parts[0]
    elif len(parts) == 2:
        # start:end
        start_str, end_str = parts
    elif len(parts) == 3:
        # start:step:end
        start_str, step_str, end_str = parts
    else:
        # Invalid format
        return []

    # Parse the numbers to integers
    try:
        start = int(start_str) if start_str != "" else anim_start
        step = int(step_str) if step_str != "" else 1
        end = int(end_str) if end_str != "" else anim_end
    except (ValueError, TypeError):
        # Invalid number format in slice string
        return []

    # Invalid format
    if step <= 0:
        return []

    # Evaluate the range
    current_frame = start
    if start > end:
        return []
    while current_frame <= end:
        if anim_start <= current_frame <= anim_end:
            frames.append(current_frame)
        current_frame += step
    return frames


def get_frames_from_frame_ranges(
        slice_str: str, anim_start: int, anim_end: int) -> tuple[list[int], dict[str, int]]:
    """
    Splits a string by commas assuming that each part is a frame range
    string and evaluates these ranges using get_frames_from_frame_range to
    return a list of unique frames and a dictionary with the number of frames
    added by each range.

    :param slice_str: A string with frame ranges separated by commas.
    :param anim_start: The starting frame of the animation.
    :param anim_end: The ending frame of the animation.
    :return: A list of unique frame numbers sorted in ascending order and a
        dictionary that maps each range to the number of frames it produced.
    """
    if slice_str == "":
        return [], {}
    all_frames: set[int] = set()

    # Split by whitespaces, eliminate duplicated ranges to avoid unnecessary
    # work
    range_strs = set(i.strip() for i in slice_str.strip().split(","))
    # Evaluate and append the ranges
    frame_counts: dict[str, int] = {}
    for range_str in range_strs:
        if range_str == "":
            continue
        frames = get_frames_from_frame_range(range_str, anim_start, anim_end)
        all_frames.update(frames)
        frame_counts[range_str] = len(frames)
    return sorted(list(all_frames)), frame_counts
