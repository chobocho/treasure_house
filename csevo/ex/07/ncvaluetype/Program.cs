// 슬라이드 p7-v6-nullcond-nullable — Nullable<T> 받는 쪽, C# 6.0
using System;

class App
{
    static void Main()
    {
        DateTime? when = new DateTime(2001, 2, 3);
        int? none = null;
        Console.WriteLine("[{0}] [{1}]",
            when?.Year, when?.ToString("MM"));     // when.Value.Year
        Console.WriteLine("[{0}] [{1}]",
            none?.ToString(), none?.CompareTo(1));
#if BAD
        int plain = 5;
        Console.WriteLine(plain?.ToString());
#endif
    }
}
