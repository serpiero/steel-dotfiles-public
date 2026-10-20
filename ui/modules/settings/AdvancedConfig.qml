import QtQuick
import QtQuick.Layouts
import Quickshell
import qs.services
import qs.modules.common
import qs.modules.common.widgets

ContentPage {
    forceWidth: true

    Timer {
        id: refreshSpectrum
        interval: 1000
        onTriggered: Quickshell.execDetached(["python3", Quickshell.env("HOME")+"/.local/share/rice-profiles/palette.py", "--current"])
    }
    ContentSection {
        icon: "palette"
        title: "Steel · active palette"
        StyledText {
            Layout.fillWidth: true
            wrapMode: Text.WordWrap
            text: "Fixed #161a1f backgrounds with steel accents across the shell, browser, GTK, Qt and supported app adapters. Wallpaper changes subtly adjust the accent family."
        }
        ConfigSpinBox {
            icon: "palette"
            text: "Accent tint (%)"
            value: Config.options.appearance.obsidianTint * 100
            from: 50; to: 150; stepSize: 10
            onValueChanged: {
                if(Math.abs(Config.options.appearance.obsidianTint-value/100)<0.001)return;
                Config.options.appearance.obsidianTint=value/100;
                refreshSpectrum.restart();
            }
        }
        StyledText {
            Layout.fillWidth: true
            wrapMode: Text.WordWrap
            text: "Intelligence keeps native ChatGPT and Gemini colors; its container follows the active page."
        }
    }
    ContentSection {
        icon: "info"
        title: "Components in this fork"
        StyledText {
            Layout.fillWidth: true
            wrapMode: Text.WordWrap
            text: "Illogical Impulse: shell composition, panels, launcher and wallpaper selector.\nCybrdots: initial Hyprland decorations/groups, Kitty geometry and btop theme basis.\nObsidian: steel palette, blur rules, prompt, web panels, app adapters and capture overlay. Firefox preserves its layout; Dark Reader harmonizes web content."
        }
        StyledText {
            Layout.fillWidth: true
            wrapMode: Text.WordWrap
            text: "Illogical color harmonization inspired the palette. Its original application generator is disabled here; Obsidian uses isolated configurations and preserves KDE."
        }
    }
    ContentSection {
        icon: "colors"
        visible: false
        title: Translation.tr("Color generation")

        ConfigSwitch {
            buttonIcon: "hardware"
            text: Translation.tr("Shell & utilities")
            checked: Config.options.appearance.wallpaperTheming.enableAppsAndShell
            onCheckedChanged: {
                Config.options.appearance.wallpaperTheming.enableAppsAndShell = checked;
            }
        }
        ConfigSwitch {
            buttonIcon: "tv_options_input_settings"
            text: Translation.tr("Qt apps")
            checked: Config.options.appearance.wallpaperTheming.enableQtApps
            onCheckedChanged: {
                Config.options.appearance.wallpaperTheming.enableQtApps = checked;
            }
            StyledToolTip {
                text: Translation.tr("Shell & utilities theming must also be enabled")
            }
        }
        ConfigSwitch {
            buttonIcon: "terminal"
            text: Translation.tr("Terminal")
            checked: Config.options.appearance.wallpaperTheming.enableTerminal
            onCheckedChanged: {
                Config.options.appearance.wallpaperTheming.enableTerminal = checked;
            }
            StyledToolTip {
                text: Translation.tr("Shell & utilities theming must also be enabled")
            }
        }
        ConfigRow {
            uniform: true
            ConfigSwitch {
                buttonIcon: "dark_mode"
                text: Translation.tr("Force dark mode in terminal")
                checked: Config.options.appearance.wallpaperTheming.terminalGenerationProps.forceDarkMode
                onCheckedChanged: {
                     Config.options.appearance.wallpaperTheming.terminalGenerationProps.forceDarkMode= checked;
                }
                StyledToolTip {
                    text: Translation.tr("Ignored if terminal theming is not enabled")
                }
            }
        }

        ConfigSpinBox {
            icon: "invert_colors"
            text: Translation.tr("Terminal: Harmony (%)")
            value: Config.options.appearance.wallpaperTheming.terminalGenerationProps.harmony * 100
            from: 0
            to: 100
            stepSize: 10
            onValueChanged: {
                Config.options.appearance.wallpaperTheming.terminalGenerationProps.harmony = value / 100;
            }
        }
        ConfigSpinBox {
            icon: "gradient"
            text: Translation.tr("Terminal: Harmonize threshold")
            value: Config.options.appearance.wallpaperTheming.terminalGenerationProps.harmonizeThreshold
            from: 0
            to: 100
            stepSize: 10
            onValueChanged: {
                Config.options.appearance.wallpaperTheming.terminalGenerationProps.harmonizeThreshold = value;
            }
        }
        ConfigSpinBox {
            icon: "format_color_text"
            text: Translation.tr("Terminal: Foreground boost (%)")
            value: Config.options.appearance.wallpaperTheming.terminalGenerationProps.termFgBoost * 100
            from: 0
            to: 100
            stepSize: 10
            onValueChanged: {
                Config.options.appearance.wallpaperTheming.terminalGenerationProps.termFgBoost = value / 100;
            }
        }
    }



}
