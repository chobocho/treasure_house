// 슬라이드 p12-v11-math-parse — T.Parse 의 오버로드 함정, C# 11.0
using System;
using System.Globalization;
using System.Numerics;

class App
{
    // IParsable<T>: Parse(string, IFormatProvider) — no 1-arg form
    static T P<T>(string s) where T : IParsable<T> =>
        T.Parse(s, CultureInfo.InvariantCulture);

    // INumberBase<T> adds a NumberStyles overload
    static T Hex<T>(string s) where T : INumberBase<T> =>
        T.Parse(s, NumberStyles.HexNumber,
            CultureInfo.InvariantCulture);

#if BAD
    static T Short<T>(string s) where T : INumber<T> => T.Parse(s);
#endif

    static void Main()
    {
        Console.WriteLine(P<int>("12") + " " + P<double>("1.5"));
        Console.WriteLine(P<DateOnly>("2022-11-08").DayOfWeek);
        Console.WriteLine(P<TimeSpan>("1:30:00").TotalMinutes);
        Console.WriteLine(Hex<int>("ff") + " "
            + Hex<long>("7fffffffffffffff"));
        Console.WriteLine(int.Parse("12"));   // the type itself has it
    }
}
