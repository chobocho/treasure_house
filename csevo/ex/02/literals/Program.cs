// 슬라이드 p2-v1-literals — 정수 리터럴의 형식은 값이 정한다, C# 1.0
using System;

class App
{
    static void Show(string text, object value)
    {
        Console.WriteLine(text.PadRight(13) + value.GetType().Name);
    }

    static void Main()
    {
        Show("2147483647", 2147483647);
        Show("2147483648", 2147483648);       // too big for int
        Show("4294967296", 4294967296);       // too big for uint
        Show("0xFFFFFFFF", 0xFFFFFFFF);
        Show("1L", 1L);
        Show("1U", 1U);
        Show("1UL", 1UL);
        Show("1.0", 1.0);
        Show("1.0F", 1.0F);
        Show("1.0M", 1.0M);
        Show("1E3", 1E3);
        Show("'x'", 'x');
        Show("-2147483648", -2147483648);     // minus applied to uint?
    }
}
