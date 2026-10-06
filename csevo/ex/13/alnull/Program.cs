// 슬라이드 p13-v12-al-null — string? 은 별칭이 못 된다, C# 12.0
using System;
using System.Collections.Generic;
using MaybeInt = int?;                         // nullable value type
using Names = System.Collections.Generic.List<string?>;
#if BAD
using MaybeName = string?;                     // top-level string?
#endif

class App
{
    static void Main()
    {
        MaybeInt n = null;
        Names names = ["a", null];
        Console.WriteLine($"{n ?? -1} {names.Count}");
        Console.WriteLine(typeof(MaybeInt).Name);
    }
}
