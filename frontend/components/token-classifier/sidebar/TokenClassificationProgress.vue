<!--
  - coding=utf-8
  - Copyright 2021-present, the Recognai S.L. team.
  -
  - Licensed under the Apache License, Version 2.0 (the "License");
  - you may not use this file except in compliance with the License.
  - You may obtain a copy of the License at
  -
  -     http://www.apache.org/licenses/LICENSE-2.0
  -
  - Unless required by applicable law or agreed to in writing, software
  - distributed under the License is distributed on an "AS IS" BASIS,
  - WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
  - See the License for the specific language governing permissions and
  - limitations under the License.
  -->

<template>
  <sidebar-progress :dataset="dataset">
    <ul v-if="annotationsProgress" class="metrics__list">
      <li v-for="(counter, label) in getInfo" :key="label">
        <template v-if="counter > 0">
          <entity-label
            :label="label"
            :color="`color_${
              entities.filter((e) => e.text === label)[0].colorId %
              $entitiesMaxColors
            }`"
          />
          <span class="metrics__list__counter">{{
            counter | formatNumber
          }}</span>
        </template>
      </li>
    </ul>
  </sidebar-progress>
</template>

<script>
import { AnnotationProgress } from "@/models/AnnotationProgress";
export default {
  props: {
    dataset: {
      type: Object,
      required: true,
    },
  },
  computed: {
    getInfo() {
      return this.annotationsProgress.annotatedAs;
    },
    annotationsProgress() {
      return AnnotationProgress.find(this.dataset.name);
    },
    entities() {
      return this.dataset.entities;
    },
  },
};
</script>
<style lang="scss" scoped></style>
