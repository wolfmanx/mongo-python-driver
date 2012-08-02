:mod:`context` -- BSON Encoding/Decoding Context
================================================

.. automodule:: bson.context
   :synopsis: BSON Encoding/Decoding Context

   .. autofunction:: lock
   .. autofunction:: unlock
   .. autofunction:: get_context
   .. autofunction:: set_context
   .. autofunction:: enable_threading
   .. autofunction:: is_threading_enabled
   .. autofunction:: dbg_check_context
   .. autofunction:: dbg_check_context_required
   .. autofunction:: export_to_bson

   .. autoclass:: Context([context=None])
      :members:
      :show-inheritance:

   .. autoclass:: ChildContext([default=False])
      :members:
      :show-inheritance:

   .. autoclass:: ThreadContext()
      :members:
      :show-inheritance:
