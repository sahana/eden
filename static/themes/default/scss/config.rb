# Build configuration for Compass
#
# To build the debug versions, use:
#   compass compile
#
# To build the minified versions, use:
#   compass compile -e production
#

# Require any additional compass plugins here:

# Import path:
add_import_path "../../foundation/scss/components"

# Paths:
http_path = "/"
css_dir = (environment == :production) ? "../foundation/prod" : "../foundation"
sass_dir = "."
images_dir = "images"
javascripts_dir = "js"

# Preferred output style (can be overridden via the command line):
# output_style = :expanded or :nested or :compact or :compressed
output_style = (environment == :production) ? :compressed : :expanded

# Debugging comments that display the original location of selectors:
line_comments = (environment == :production) ? false : true

# Post-process production versions
if environment == :production
    on_stylesheet_saved do |f|
        # Rename into *.min.css and move up one folder
        FileUtils.mv f, "#{File.dirname(File.dirname(f))}/#{File.basename(f,'.*')}.min.css"
        # Remove the "prod" folder
        FileUtils.rm_rf(File.dirname(f))
    end
end
