from enum import Enum
from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.util import Cm, Pt


class SlideLayout(Enum):
    TITLE_SLIDE = 0
    TITLE_AND_CONTENT = 1
    SECTION_HEADER = 2
    TWO_CONTENT = 3
    COMPARISON = 4
    TITLE_ONLY = 5
    BLANK = 6
    CONTENT_WITH_CAPTION = 7
    PICTURE_WITH_CAPTION = 8


def create_powerpoint(data: dict, file_path: Path):
    prs = Presentation()

    title_slide_layout = prs.slide_layouts[SlideLayout.TITLE_SLIDE.value]
    title_and_content_layout = prs.slide_layouts[SlideLayout.TITLE_AND_CONTENT.value]
    title_only_layout = prs.slide_layouts[SlideLayout.TITLE_ONLY.value]

    # Set size. Lengths are measured in EMU.  360,000 EMU = 1 cm.  So 1 mm = 36,000 EMU.
    # A4 page is 210 mm x 297 mm.  A4 Landscape is 297x210 mm, or 10,692,000 x 7,560,000 EMU.
    prs.slide_width = 297 * 36000  # A4 Landscape width.
    prs.slide_height = 210 * 36000  # A4 Landscape height.

    BLOCKWISE_GREEN = RGBColor(0x12, 0x6f, 0x43)

    ###########################################################################

    title_slide = prs.slides.add_slide(slide_layout=title_slide_layout)

    for shape in title_slide.placeholders:
        print(shape.placeholder_format.idx, shape.name)

    logo = title_slide.shapes.add_picture("Blockwise_Services_logo.png", left=Cm(3), top=Cm(0.5), height=Cm(10))

    print()
    for shape in title_slide.shapes:
        print(shape)
        # print(shape.placeholder_format.idx, shape.name)

    title = title_slide.placeholders[0]
    subtitle = title_slide.placeholders[1]
    title.top = Cm(10.5)
    subtitle.top = Cm(15)

    text_frame = title.text_frame
    para = text_frame.paragraphs[0]
    para.alignment = PP_ALIGN.RIGHT
    run = para.add_run()
    run.text = "Farm Name Here"
    run.font.size = Pt(36)
    run.font.bold = True
    run.font.name = "Assistant"
    run.font.color.rgb = BLOCKWISE_GREEN

    para = text_frame.add_paragraph()
    para.alignment = PP_ALIGN.RIGHT
    run = para.add_run()
    run.text = "Spring 2026"
    run.font.size = Pt(36)
    run.font.bold = True
    run.font.name = "Assistant"
    run.font.color.rgb = BLOCKWISE_GREEN

    para = text_frame.add_paragraph()
    para.alignment = PP_ALIGN.RIGHT
    run = para.add_run()
    run.text = "Wise Production Report"
    run.font.size = Pt(16)
    run.font.bold = False
    run.font.name = "Assistant"
    run.font.color.rgb = BLOCKWISE_GREEN

    # title.text = "Farm Name Here"
    # subtitle.text = "Wise Production Report"

    ##########################################################################################

    slide_1 = prs.slides.add_slide(slide_layout=title_and_content_layout)

    title = slide_1.placeholders[0]
    run = title.text_frame.paragraphs[0].add_run()
    run.text = "Wise Production Report"
    run.font.size = Pt(36)
    run.font.color.rgb = BLOCKWISE_GREEN

    content = slide_1.placeholders[1]

    p1 = content.text_frame.paragraphs[0]
    p1.text = ("Utilising your milk recording data for the completed lactation, "
               "we have assessed the performance of individual animals.")
    p1.runs[0].font.size = Pt(15)

    p2 = content.text_frame.add_paragraph()
    p2.text = ("The profitability of your dairy herd depends on having cows that are consistently high performers "
               "over their lifetime in the following areas:")
    p2.runs[0].font.size = Pt(15)

    p2_1 = content.text_frame.add_paragraph()
    p2_1.level = 2
    label = p2_1.add_run()
    label.text = "Production:  "
    label.font.size = Pt(15)
    label.font.bold = True
    label.font.color.rgb = BLOCKWISE_GREEN
    desc = p2_1.add_run()
    desc.text = "High production of milk solids."
    desc.font.size = Pt(15)

    p2_2 = content.text_frame.add_paragraph()
    p2_2.level = 2
    label = p2_2.add_run()
    label.text = "Efficiency:  "
    label.font.size = Pt(15)
    label.font.bold = True
    label.font.color.rgb = BLOCKWISE_GREEN
    desc = p2_2.add_run()
    desc.text = ("Efficiently converts grass into milk solids, estimated by kilograms of milk solids per "
                 "kilogram of cow liveweight.")
    desc.font.size = Pt(15)

    p2_3 = content.text_frame.add_paragraph()
    p2_3.level = 2
    label = p2_3.add_run()
    label.text = "Health:  "
    label.font.size = Pt(15)
    label.font.bold = True
    label.font.color.rgb = BLOCKWISE_GREEN
    desc = p2_3.add_run()
    desc.text = "Healthy as measured by low Somatic Cell Count (SCC)."
    desc.font.size = Pt(15)

    p2_4 = content.text_frame.add_paragraph()
    p2_4.level = 2
    label = p2_4.add_run()
    label.text = "Fertility:  "
    label.font.size = Pt(15)
    label.font.bold = True
    label.font.color.rgb = BLOCKWISE_GREEN
    desc = p2_4.add_run()
    desc.text = "In calf every year."
    desc.font.size = Pt(15)

    p3 = content.text_frame.add_paragraph()
    p3.text = ("We have used actual cow liveweight data if available.  If it is not available, we use the following "
               "standard estimates for cow liveweights:")
    p3.runs[0].font.size = Pt(15)

    p3_1 = content.text_frame.add_paragraph()
    p3_1.level = 2
    label = p3_1.add_run()
    label.text = "450 kg "
    label.font.size = Pt(15)
    label.font.bold = True
    label.font.color.rgb = BLOCKWISE_GREEN
    desc = p3_1.add_run()
    desc.text = "for cows in Lactation 1."
    desc.font.size = Pt(15)

    p3_2 = content.text_frame.add_paragraph()
    p3_2.level = 2
    label = p3_2.add_run()
    label.text = "500 kg "
    label.font.size = Pt(15)
    label.font.bold = True
    label.font.color.rgb = BLOCKWISE_GREEN
    desc = p3_2.add_run()
    desc.text = "for cows in Lactation 2 or higher."
    desc.font.size = Pt(15)

    ###########################################################################################################
    # Summary Table

    slide_2 = prs.slides.add_slide(slide_layout=title_only_layout)

    title = slide_2.placeholders[0]
    run = title.text_frame.paragraphs[0].add_run()
    run.text = "Lactation"
    run.font.size = Pt(36)
    run.font.color.rgb = BLOCKWISE_GREEN

    shape_with_table = slide_2.shapes.add_table(rows=10, cols=11, left=Cm(2), top=Cm(4), width=Cm(26), height=Cm(8))
    table = shape_with_table.table

    top_cell = table.cell(0, 0)
    top_cell.merge(table.cell(0, 10))
    top_cell.text = "Milking Herd 2025 Lactation"

    column_names = ("Lactation", "No of Cows", "% of Herd", "Vol of Milk kg", "Avg Vol of Milk", "Milk Solids kg",
                    "Avg Milk Solids", "Days in Milk", "Avg Weight", "Avg Fat %", "Avg Protein %")

    for idx, name in enumerate(column_names):
        table.cell(1, idx).text = name
        table.cell(1, idx).text_frame.paragraphs[0].font.size = Pt(10)
        table.cell(1, idx).text_frame.paragraphs[0].font.bold = True
        # table.cell(1, idx).text_frame.paragraphs[0].font.fill.back_color = BLOCKWISE_GREEN
        table.cell(7, idx).text = name
        table.cell(7, idx).text_frame.paragraphs[0].font.size = Pt(10)
        table.cell(7, idx).text_frame.paragraphs[0].font.bold = True


    prs.save(file_path)


if __name__ == "__main__":
    src_file_path = Path(__file__).parent.parent.parent
    file_path = src_file_path.joinpath("temp", "cowpoke", "herd_improvement", "blockwise_herd_report.pptx")
    create_powerpoint(data={}, file_path=file_path)
