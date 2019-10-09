--
-- look_newviolet for Notion's default drawing engine. 
-- Based on look_cleanviolet
-- 

if not gr.select_engine("de") then
    return
end

de.reset()

de.defstyle("*", {
    highlight_colour = "#e7e7ff",
    shadow_colour = "#e7e7ff",
    background_colour = "#b8b8c8",
    foreground_colour = "#000000",
    
    shadow_pixels = 0,
    highlight_pixels = 0,
    padding_pixels = 0,
    spacing = 1,
    border_style = "elevated",
    border_sides = "tb",
    
    font = "-*-helvetica-medium-r-normal-*-14-*-*-*-*-*-*-*",
    text_align = "center",
})


de.defstyle("tab", {
    font = "-*-helvetica-medium-r-normal-*-12-*-*-*-*-*-*-*",
    
    de.substyle("active-selected", {
        highlight_colour = "#000000",
        shadow_colour = "#000000",
        background_colour = "#000000",
        foreground_colour = "#000040",
    }),

    de.substyle("inactive-selected", {
        highlight_colour = "#000000",
        shadow_colour = "#000000",
        background_colour = "#000000",
        foreground_colour = "#000040",
    }),
})


de.defstyle("input", {
    text_align = "left",
    highlight_colour = "#eeeeff",
    shadow_colour = "#eeeeff",
    
    de.substyle("*-selection", {
        background_colour = "#666699",
        foreground_colour = "#000000",
    }),

    de.substyle("*-cursor", {
        background_colour = "#000000",
        foreground_colour = "#b8b8c8",
    }),
})


de.defstyle("input-menu", {
    highlight_pixels = 0,
    shadow_pixels = 0,
    padding_pixels = 0,
})


de.defstyle("frame", {
    shadow_pixels = 0,
    highlight_pixels = 0,
    padding_pixels = 0,
    border_sides = "all",
})


dopath("lookcommon_clean")


-- Refresh objects' brushes.
gr.refresh()
