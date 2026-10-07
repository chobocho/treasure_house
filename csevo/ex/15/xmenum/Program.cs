// 슬라이드 p15-v14-xm-enum — 열거형에 붙이는 확장 속성, C# 14
using System;

enum Size { Small, Medium, Large }

static class SizeExt
{
    extension(DayOfWeek d)
    {
        public bool IsWeekend =>
            d == DayOfWeek.Saturday || d == DayOfWeek.Sunday;
    }

    extension(DayOfWeek)
    {
        public static DayOfWeek First => DayOfWeek.Monday;
    }

    extension(Size)
    {
        public static Size Large => Size.Small;   // hidden by member
        public static Size Default => Size.Medium;
    }
}

class Program
{
    static void Main()
    {
        Console.WriteLine(DayOfWeek.Sunday.IsWeekend + " "
            + DayOfWeek.First + " " + DayOfWeek.First.IsWeekend);
        Console.WriteLine(Size.Large + " " + Size.Default);
    }
}
