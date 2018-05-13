"""
Author: Ron Lockwood-Childs

Licensed under LGPL v2.1 (see file COPYING for details)

Pygame maker drawing primitives.
"""

import pygame
import pygame_maker.support.coordinate as coordinate

LINE_TYPES = ("dotted", "dashed", "solid", "double", "groove", "ridge", "inset", "outset")

DASHED_LINE_SEGMENT_LENGTH = 10
DASHED_LINE_SEGMENT_GAP = 10
DOTTED_LINE_SEGMENT_LENGTH = 2
DOTTED_LINE_SEGMENT_GAP = 10
DOUBLE_LINE_GAP = 1


def _divide_extra_segment_padding(length, padding_needed):
    # padding should be added as evenly as possible, but any extra pixels
    # should be preferred at start or end
    if length == 1:
        return [padding_needed]
    odd_padding = False
    if padding_needed % 2 != 0:
        odd_padding = True
    if length == 2:
        padding_ary = [padding_needed / 2, padding_needed / 2]
        if odd_padding:
            padding_ary[0] += 1
        return padding_ary
    base_padding = padding_needed / length
    current_padding = length * base_padding
    leftover_padding = padding_needed - current_padding
    padding_ary = [base_padding]*length
    mid_idx = length / 2
    pad_count = 0
    if leftover_padding == 1:
        padding_ary[mid_idx] += 1
        pad_count += 1
    elif leftover_padding > 1:
        # spread out leftovers as evenly as possible
        for idx in range(length/2):
            for alternate in [(1, 0), (-1, 1)]:
                pad_idx = alternate[0] * (idx + alternate[1])
                padding_ary[pad_idx] += 1
                pad_count += 1
                if pad_count >= leftover_padding:
                    break
            if pad_count >= leftover_padding:
                break
    if pad_count < leftover_padding:
        if (leftover_padding - pad_count) > 1:
            print("_divide_extra_segment_padding(): Too much leftover padding")
        padding_ary[mid_idx] += 1
    return padding_ary

def draw_line_segments(surface, line_properties):
    """Draw horizontal or vertical lines in dotted or dashed styles."""
    if line_properties["start"] == line_properties["end"]:
        print("draw_line_segments(): Line starts and ends at the same coordinate")
        return
    if line_properties["width"] == 0:
        print("draw_line_segments(): Line has 0 width")
        return
    line_slope_y = abs(line_properties["end"].y - line_properties["start"].y)
    line_slope_x = abs(line_properties["end"].x - line_properties["start"].x)
    seg_len = DASHED_LINE_SEGMENT_LENGTH
    seg_gap = DASHED_LINE_SEGMENT_GAP
    if line_properties["style"] == "dotted":
        seg_len = line_properties["width"] + 1
        seg_gap = DOTTED_LINE_SEGMENT_GAP
    elif line_properties["style"] != "dashed":
        print(("draw_line_segments(): Line style '{}' is not segmented".
              format(line_properties["style"])))
        return
    sqrd_length = (line_slope_x * line_slope_x) + (line_slope_y * line_slope_y)
    sqrd_full_gap_len = (seg_len * 2 + seg_gap) * (seg_len * 2 + seg_gap)
    # divide up all but the final segment between segment + gap pairs
    seg_count = (line_slope_x - seg_len) / (seg_len + seg_gap)
    if line_slope_x == 0:
        seg_count = (line_slope_y - seg_len) / (seg_len + seg_gap)
    if sqrd_length <= (seg_len * seg_len):
        # not enough space for a gap, just draw between the two points
        pygame.draw.line(surface, line_properties["color"].color,
                         (line_properties["start"].x, line_properties["start"].y),
                         (line_properties["end"].x, line_properties["end"].y),
                         line_properties["width"])
    elif (sqrd_length < sqrd_full_gap_len) or (seg_count < 1):
        # not enough space for a normal gap, just draw a small gap mid-way
        # between the two points
        midpoint1 = coordinate.Coordinate(line_properties["start"].x + line_slope_x/2,
                                          line_properties["start"].y + line_slope_y/2)
        midpoint2 = midpoint1.copy()
        if line_slope_x > 4:
            midpoint1.x -= 1
            midpoint2.x += 1
        if line_slope_y > 4:
            midpoint1.y -= 1
            midpoint2.y += 1
        pygame.draw.line(surface, line_properties["color"].color,
                         (line_properties["start"].x, line_properties["start"].y),
                         (midpoint1.x, midpoint1.y),
                         line_properties["width"])
        pygame.draw.line(surface, line_properties["color"].color,
                         (midpoint2.x, midpoint2.y),
                         (line_properties["end"].x, line_properties["end"].y),
                         line_properties["width"])
    elif line_slope_y == 0:
        # simple horizontal line
        # if the leftover space is larger than the final segment, add
        # extra padding between other segments
        last_gap = (line_slope_x - seg_len) - (seg_count * (seg_len + seg_gap))
        # divide up the extra pixels evenly in extra padding
        extra_pad = _divide_extra_segment_padding(seg_count, last_gap)
        # print(" extra pad {}".format(extra_pad))
        seg_idx = 0
        y_pos = line_properties["start"].y
        x_seg_posn = line_properties["start"].x
        # draw all line segments segments plus gaps that will fit
        while x_seg_posn < line_properties["end"].x - seg_len - 1:
            pygame.draw.line(surface, line_properties["color"].color, (x_seg_posn, y_pos),
                             (x_seg_posn + seg_len, y_pos), line_properties["width"])
            x_seg_posn += seg_len + seg_gap
            if extra_pad is not None:
                x_seg_posn += extra_pad[seg_idx]
            seg_idx += 1
        # draw the last segment
        pygame.draw.line(surface, line_properties["color"].color,
                         (line_properties["end"].x - seg_len, line_properties["end"].y),
                         (line_properties["end"].x, line_properties["end"].y),
                         line_properties["width"])
    elif line_slope_x == 0:
        # simple vertical line
        last_gap = (line_slope_y - seg_len) - (seg_count * (seg_len + seg_gap))
        # divide up the extra pixels evenly in extra padding
        extra_pad = _divide_extra_segment_padding(seg_count, last_gap)
        # print(" extra pad {}".format(extra_pad))
        seg_idx = 0
        x_pos = line_properties["start"].x
        y_seg_posn = line_properties["start"].y
        # draw all line segments segments plus gaps that will fit
        while y_seg_posn < line_properties["end"].y - seg_len - 1:
            pygame.draw.line(surface, line_properties["color"].color, (x_pos, y_seg_posn),
                             (x_pos, y_seg_posn + seg_len), line_properties["width"])
            y_seg_posn += seg_len + seg_gap
            if extra_pad is not None:
                y_seg_posn += extra_pad[seg_idx]
            seg_idx += 1
        # draw the last segment
        pygame.draw.line(surface, line_properties["color"].color,
                         (line_properties["end"].x, line_properties["end"].y - seg_len),
                         (line_properties["end"].x, line_properties["end"].y),
                         line_properties["width"])
    else:
        # y_intercept = line_properties["start"].y - (float(line_slope_y) * \
        #     line_properties["start"].x) / float(line_slope_x)
        print("draw_line_segments(): diagonal line segments NYI")

def draw_line(surface, line_start, line_end, width, color, style):
    """
    Draw a line on the supplied surface between two points, using the given width,
    color, and style.

    :param surface: The surface the line will be drawn upon
    :type surface: :py:class:`pygame.Surface`
    :param line_start: The coordinate of the start of the line
    :type line_start: :py:class:`~pygame_maker.support.coordinate.Coordinate`
    :param line_end: The coordinate of the end of the line
    :type line_start: :py:class:`~pygame_maker.support.coordinate.Coordinate`
    :param width: The line's width in pixels
    :type width: int
    :param color: The line's color
    :type color: :py:class:`~pygame_maker.support.color.Color`
    :param style: The line's type (dashed, solid, etc.)
    :type style: str
    """
    if line_start == line_end:
        print("draw_line(): Line starts and ends at the same coordinate")
        return
    if width == 0:
        print("draw_line(): Line has 0 width")
        return
    line_properties = {"start": line_start, "end": line_end, "width": width,
                       "color": color, "style": style}
    if line_properties["style"] in ("dotted", "dashed"):
        draw_line_segments(surface, line_properties)
    elif line_properties["style"] in ("solid", "double"):
        # let the caller handle the "double" style by drawing it twice with
        # different start/end points, since only the caller knows whether
        # other double lines intersect with this one
        pygame.draw.line(surface, color.color, (line_start.x, line_start.y),
                         (line_end.x, line_end.y), width)
    elif line_properties["style"] in ("groove", "ridge", "inset", "outset"):
        print("draw_line(): Line style '{}' NYI".format(style))
    else:
        print("draw_line(): Unknown line style '{}'".format(line_properties["style"]))

