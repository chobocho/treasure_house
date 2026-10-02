// 슬라이드 p7-v6-us-enum — 열거형 멤버와 중첩 형식, C# 6.0
using System;
using static System.DayOfWeek;
using static Shapes;
#if BAD
using static System.StringSplitOptions;   // also has None
using static System.Base64FormattingOptions;
#endif

static class Shapes
{
    public class Square
    {
        public int Side = 2;
    }
}

class Program
{
    static bool IsWeekend(DayOfWeek d) => d == Saturday || d == Sunday;

    static void Main()
    {
        Console.WriteLine(IsWeekend(Monday) + " " + IsWeekend(Sunday));
        Square s = new Square();           // nested type, no "Shapes."
        Console.WriteLine(s.Side);
#if BAD
        Console.WriteLine(None);
#endif
    }
}
