/* Included after Ozone's built-in themes. Read only display colors from the rice. */
static void obsidian_quad(float *quad, unsigned rgb)
{
   unsigned vertex;
   for (vertex=0; vertex<4; vertex++)
   {
      quad[vertex*4+0]=((rgb>>16)&255)/255.0f;
      quad[vertex*4+1]=((rgb>>8)&255)/255.0f;
      quad[vertex*4+2]=(rgb&255)/255.0f;
      quad[vertex*4+3]=1.0f;
   }
}
static bool obsidian_palette_reload(void)
{
   static unsigned ticks=0;
   static ino_t inode=0;
   static time_t modified=0;
   const char *path=getenv("OBSIDIAN_RETROARCH_PALETTE");
   struct stat info;
   FILE *file;
   char key[48];
   unsigned color;
   if (!path || (ticks++%30)!=0 || stat(path,&info)!=0) return false;
   if (inode==info.st_ino && modified==info.st_mtime) return false;
   file=fopen(path,"r");
   if (!file) return false;
   inode=info.st_ino;modified=info.st_mtime;
   while (fscanf(file,"%47s %x",key,&color)==2)
   {
      if (strcmp(key,"background")==0)
      {
         obsidian_quad(ozone_theme_dark.background,color);
         obsidian_quad(ozone_sidebar_background_dark,color);
         obsidian_quad(ozone_sidebar_gradient_top_dark,color);
         obsidian_quad(ozone_sidebar_gradient_bottom_dark,color);
         obsidian_quad(ozone_background_libretro_running_dark,color);
      }
      else if (strcmp(key,"high")==0)
      {
         obsidian_quad(ozone_theme_dark.header_footer_separator,color);
         obsidian_quad(ozone_theme_dark.entries_border,color);
      }
      else if (strcmp(key,"text")==0)
      {
         obsidian_quad(ozone_theme_dark.text,color);
         obsidian_quad(ozone_theme_dark.entries_icon,color);
         ozone_theme_dark.text_rgba=(color<<8)|255;
         ozone_theme_dark.text_sidebar_rgba=(color<<8)|255;
      }
      else if (strcmp(key,"selection")==0) obsidian_quad(ozone_theme_dark.selection,color);
      else if (strcmp(key,"accent")==0)
      {
         obsidian_quad(ozone_theme_dark.selection_border,color);
         obsidian_quad(ozone_theme_dark.text_selected,color);
         obsidian_quad(ozone_border_0_dark,color);
         ozone_theme_dark.text_selected_rgba=(color<<8)|255;
         ozone_theme_dark.screensaver_tint=color;
      }
      else if (strcmp(key,"accent_pressed")==0) obsidian_quad(ozone_border_1_dark,color);
      else if (strcmp(key,"elevated")==0) obsidian_quad(ozone_theme_dark.message_background,color);
      else if (strcmp(key,"muted")==0) ozone_theme_dark.text_sublabel_rgba=(color<<8)|255;
   }
   fclose(file);
   return true;
}
