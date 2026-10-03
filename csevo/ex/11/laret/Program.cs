// 슬라이드 p11-v10-la-ret — 람다의 명시적 반환 형식, C# 10.0
using System;

class App
{
    static string Of<T>(Func<T> f) => typeof(T).Name;

    static void Main()
    {
        // b ? 1 : null has no type of its own: say the return type
        var len = int? (string s) => s.Length > 0 ? s.Length : null;
        var first = ref int (int[] a) => ref a[0];    // ref return
        var nums = new[] { 1, 2 };
        first(nums) = 10;                             // writes nums[0]

        Console.WriteLine(len.GetType());
        Console.WriteLine($"{len("abc")} [{len("")}] {nums[0]}");
        Console.WriteLine(first.GetType().Name);
        // method type inference: exact inference from the return type
        Console.WriteLine(Of(() => 1) + " " + Of(long () => 1));
        Console.WriteLine(Of(object () => "s"));
#if BAD
        var plain = (string s) => s.Length > 0 ? s.Length : null;
        Func<object> f1 = string () => null;          // no variance
#endif
    }
}
