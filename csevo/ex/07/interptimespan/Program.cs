// 슬라이드 p7-v6-interp-colon — 서식 안의 콜론과 역슬래시, C# 6.0
using System;

class App
{
    static void Main()
    {
        TimeSpan t = new TimeSpan(1, 2, 3);
        DateTime d = new DateTime(2001, 2, 3, 4, 5, 6);
        Console.WriteLine($"{d:HH:mm:ss}");      // first ':' starts it
        Console.WriteLine($"{t:hh\\:mm}");       // \\ in a regular $""
        Console.WriteLine($@"{t:hh\:mm}");       // \ in a verbatim $@""
        try
        {
            Console.WriteLine($"{t:hh:mm}");     // TimeSpan needs \:
        }
        catch (FormatException e)
        {
            Console.WriteLine("FormatException: " + e.Message);
        }
#if BAD
        Console.WriteLine($"{t:hh\:mm}");
#endif
    }
}
