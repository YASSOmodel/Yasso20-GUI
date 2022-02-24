# (C) Copyright 2005-2021 Enthought, Inc., Austin, TX
# All rights reserved.
#
# This software is provided without warranty under the terms of the BSD
# license included in LICENSE.txt and may be redistributed only under
# the conditions described in the aforementioned license. The license
# is also available online at http://www.enthought.com/licenses/BSD.txt
#
# Thanks for using Enthought open source!

import sys


from traits.api import provides


from pyface.tasks.i_editor_area_pane import IEditorAreaPane
from .editor_area_pane import EditorAreaPane

# ----------------------------------------------------------------------------
# 'AdvancedEditorAreaPane' class.
# ----------------------------------------------------------------------------


@provides(IEditorAreaPane)
class SplitEditorAreaPane(EditorAreaPane):
    """ The toolkit-specific implementation of an AdvancedEditorAreaPane.

    See the IAdvancedEditorAreaPane interface for API documentation.
    """

    # No additional functionality over the standard EditorAreaPane in wx yet.
