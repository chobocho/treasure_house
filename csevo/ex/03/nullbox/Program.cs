// 슬라이드 p3-v2-nullable-boxing — nullable 의 박싱과 언박싱, C# 2.0
using System;

class App
{
    static void Main()
    {
        int? a = 5;
        int? n = null;
        object oa = a;                    // boxes the int itself
        object on = n;                    // boxes to a null reference
        Console.WriteLine(oa.GetType());
        Console.WriteLine(on == null);

        int? back = (int?)oa;             // unbox to int? works
        int? none = (int?)on;             // null unboxes to null
        Console.WriteLine(back + " " + none.HasValue);
        Console.WriteLine((int?)(object)7 + " " + (oa is int?));
        try
        {
            int bad = (int)on;            // null unboxed to int
            Console.WriteLine(bad);
        }
        catch (NullReferenceException e)
        {
            Console.WriteLine(e.GetType().Name);
        }
    }
}
