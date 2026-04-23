# Jian Zhang Homepage

Personal academic homepage for Jian Zhang: [jzh15.github.io](https://jzh15.github.io/).

## Overview

This repository contains the source for my personal website, including:

- homepage and biography
- selected publications and project pages
- CV and contact links
- research updates in 3D vision, spatial reasoning, and embodied intelligence

## Featured Project

### SpatialStack

Layered geometry-language fusion for 3D VLM spatial reasoning.

[Project Page](https://spatial-stack.github.io/)  
[Paper](https://arxiv.org/abs/2603.27437)  
[Code](https://github.com/jzh15/SpatialStack)  
[Model](https://huggingface.co/Journey9ni/SpatialStack-Qwen2.5-4B)  
[Data](https://huggingface.co/datasets/Journey9ni/SpatialStackData)

## Other Recent Projects

- [VLM-3R](https://vlm-3r.github.io/): vision-language models augmented with instruction-aligned 3D reconstruction
- [DynamicVerse](https://dynamic-verse.github.io/): physically-aware multimodal framework for 4D world modeling
- [Large Spatial Model](https://largespatialmodel.github.io/): end-to-end unposed images to semantic 3D
- [InstantSplat](https://instantsplat.github.io/): sparse-view pose-free Gaussian splatting in seconds

## Local Development

This site is built with Jekyll on top of `al-folio`.

```bash
bundle install
bundle exec jekyll serve
```

If your environment does not have the required Bundler version from `Gemfile.lock`, install that first.
