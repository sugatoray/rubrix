#  coding=utf-8
#  Copyright 2021-present, the Recognai S.L. team.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
from enum import Enum
from typing import List, Tuple, Union

import numpy as np

from rubrix import logging
from rubrix.client.models import TextClassificationRecord

_LOGGER = logging.getLogger(__name__)


class SortBy(Enum):
    """A tie break policy"""

    LIKELIHOOD = "likelihood"
    PREDICTION = "prediction"

    @classmethod
    def _missing_(cls, value):
        raise ValueError(
            f"{value} is not a valid {cls.__name__}, please select one of {list(cls._value2member_map_.keys())}"
        )


def find_label_errors(
    records: List[TextClassificationRecord],
    sort_by: Union[str, SortBy] = "likelihood",
    **kwargs,
) -> List[TextClassificationRecord]:
    """Find potential annotation/label errors in your records.

    It will include all records in the given list for which a prediction AND annotation is available.
    Make sure the predictions were made in a holdout manner, that is you should only include records that were not used
    in the training of the predictor.

    Args:
        records: A list of text classification records
        sort_by: One of the two options
            - "likelihood": sort the returned records by likelihood of containing a label error (most likely first)
            - "prediction": sort the returned records by the probability of the prediction (highest probability first)
        **kwargs: Passed on to `cleanlab.pruning.get_noise_indices`

    Returns:
        A list of records containing potential annotation/label errors
    """
    try:
        import cleanlab
    except ModuleNotFoundError:
        raise ModuleNotFoundError(
            "'cleanlab' must be installed to use the `find_label_errors` method! "
            "You can install 'cleanlab' with the command: `pip install cleanlab`"
        )
    else:
        from cleanlab.pruning import get_noise_indices

    if isinstance(sort_by, str):
        sort_by = SortBy(sort_by)

    _check_and_update_kwargs(records[0], sort_by, kwargs)

    # sort out only records with prediction and annotation
    records = [rec for rec in records if rec.prediction and rec.annotation]
    if not records:
        raise NoRecordsError(
            "It seems that none of your records have a prediction AND annotation!"
        )

    s, psx = _construct_s_and_psx(records)

    indices = get_noise_indices(s, psx, **kwargs)

    return np.array(records)[indices].tolist()


def _check_and_update_kwargs(record: TextClassificationRecord, sort_by: SortBy, kwargs):
    """Helper function to check and update the kwargs passed on cleanlab's `get_noise_indices`.

    Args:
        record: One of the records passed in the `find_label_error` function.
        kwargs: The passed on kwargs.

    Raises:
        ValueError: If not supported kwargs ('sorted_index_method') are passed on.
    """
    if "sorted_index_method" in kwargs:
        raise ValueError(
            "The 'sorted_index_method' kwarg is not supported, please use 'sort_by' instead."
        )
    kwargs["sorted_index_method"] = "normalized_margin"
    if sort_by is SortBy.PREDICTION:
        kwargs["sorted_index_method"] = "prob_given_label"

    if "multi_label" in kwargs:
        _LOGGER.warning(
            "You provided the kwarg 'multi_label', but it is determined automatically. "
            f"We will set it to '{record.multi_label}'."
        )
    kwargs["multi_label"] = record.multi_label


def _construct_s_and_psx(
    records: List[TextClassificationRecord],
) -> Tuple[np.ndarray, np.ndarray]:
    """Helper function to construct the s array and psx matrix.

    Args:
        records: List of records.

    Returns:
        A tuple containing the s array and the psx matrix.

    Raises:
        MissingPredictionError: If predictions are missing for certain labels.
    """
    predictions = []
    labels = set()
    for rec in records:
        predictions.append({pred[0]: pred[1] for pred in rec.prediction})
        labels.update(predictions[-1].keys())
    labels_mapping = {label: i for i, label in enumerate(labels)}

    s = (
        np.empty(len(records), dtype=object)
        if records[0].multi_label
        else np.zeros(len(records), dtype=np.short)
    )
    psx = np.zeros((len(records), len(labels)), dtype=np.float)

    for i, rec, pred in zip(range(len(records)), records, predictions):
        try:
            psx[i] = [pred[label] for label in labels]
        except KeyError as error:
            raise MissingPredictionError(
                f"It seems a prediction for {error} is missing in the following record: {rec}"
            )

        try:
            s[i] = (
                [labels_mapping[label] for label in rec.annotation]
                if rec.multi_label
                else labels_mapping[rec.annotation]
            )
        except KeyError as error:
            raise MissingPredictionError(
                f"It seems predictions are missing for the label {error}!"
            )

    return s, psx


class LabelErrorsException(Exception):
    pass


class NoRecordsError(LabelErrorsException):
    pass


class MissingPredictionError(LabelErrorsException):
    pass
