// 슬라이드 p5-v4-dyn-checked — checked 문맥도 바인더에 실린다, C# 4.0
using System;

class Program
{
    static void Main()
    {
        dynamic big = int.MaxValue;
        dynamic u = unchecked(big + 1);
        Console.WriteLine("unchecked: " + u);
        try
        {
            dynamic c = checked(big + 1);
            Console.WriteLine("checked: " + c);
        }
        catch (OverflowException e)
        {
            Console.WriteLine("checked: " + e.Message);
        }
    }
}
