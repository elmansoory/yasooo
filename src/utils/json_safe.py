"""
مساعد صغير لتسلسل JSON الآمن مع أنواع NumPy
Small helper for JSON-serializing values that may carry numpy scalar types.

بيانات تحليل الفيديو (jumps/spins/errors) تُبنى أحياناً من حسابات numpy
(np.unwrap, np.std, ...) وتحمل numpy.float64 / numpy.bool_ بدل الأنواع
الأصلية بايثون — json.dumps() لا يعرف تسلسلها فينهار البرنامج. استخدم
`default=json_numpy_default` كطبقة حماية إضافية عند أي مكان يُخزَّن فيه
ناتج تحليل حقيقي، حتى لو أصلحنا مصدر التسرب.
"""


def json_numpy_default(o):
    if hasattr(o, 'item'):  # numpy scalar (bool_, float64, int64, ...)
        return o.item()
    return str(o)
