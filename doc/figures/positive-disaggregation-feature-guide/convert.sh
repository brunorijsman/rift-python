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
mv figures-0.png diagram_clos_3pod_3leaf_3spine_4super.png
mv figures-1.png diagram_clos_3pod_3leaf_3spine_4super_intra_pod_1_failure.png
mv figures-2.png diagram_clos_3pod_3leaf_3spine_4super_inter_pod_1_failure.png
mv figures-3.png diagram_clos_3pod_3leaf_3spine_4super_inter_pod_3_failures.png

echo "Copying to S3"
for f in *.png; do
    echo $f "..."
    aws s3 cp --quiet --acl public-read $f s3://brunorijsman-public/
done
