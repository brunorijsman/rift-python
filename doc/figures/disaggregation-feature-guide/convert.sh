#! /bin/bash

# First use powerpoint to export the slides to PDF 
# Note: export to PDF, not print to PDF, otherwise trimming will not work.

if [[ ! -e figures.pdf ]]; then
    echo "PDF does not exist; export Powerpoint to PDF first (export, don't print!)"
    exit 1
fi

if [[ figures.pptx -nt figures.pdf ]]; then
    echo "Powerpoint is newer than PDF; export Powerpoint to PDF first (export, don't print!)"
    exit 1
fi

echo "Converting PDF to PNG"
magick convert -density 300 -units pixelsperinch -trim +profile "icc" figures.pdf figures.png

echo "Renaming files"
mv figures-0.png diagram-rift-typical-route-tables.png
mv figures-1.png diagram-rift-clos-3-x-3-no-failure-default-only.png
mv figures-2.png diagram-rift-clos-3-x-3-failure-pos-disagg.png
mv figures-3.png diagram-rift-clos-6x6x3-1-failure-pos-disagg.png
mv figures-4.png diagram-rift-clos-6x6x3-3-failures-pos-disagg.png
mv figures-5.png diagram-rift-multiplane-noew.png
mv figures-6.png diagram-rift-3d-planes-noew.png
mv figures-7.png diagram-rift-multiplane.png
mv figures-8.png diagram-rift-3d-planes.png
mv figures-9.png diagram-rift-neg-disagg-origination.png
mv figures-10.png diagram-rift-neg-disagg-propagation.png
mv figures-11.png diagram-rift-neg-disagg-rib.png
mv figures-12.png diagram-rift-neg-disagg-rib-to-fib.png
mv figures-13.png diagram-rift-neg-disagg-rib-and-fib.png

echo "Copying to S3"
for f in *.png; do
    echo $f "..."
    aws s3 cp --quiet --acl public-read $f s3://brunorijsman-public/
done
