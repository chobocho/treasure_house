// 슬라이드 p14-v13-idxinit — 객체 초기화자의 암시적 인덱스 ^, C# 13
using System;

public class TimerRemaining
{
    public int[] buffer { get; set; } = new int[10];
}

class Program
{
    static void Main()
    {
        var countdown = new TimerRemaining()
        {
            buffer =
            {
                [^1] = 0,
                [^2] = 1,
                [^3] = 2,
                [^4] = 3,
                [^5] = 4,
                [^6] = 5,
                [^7] = 6,
                [^8] = 7,
                [^9] = 8,
                [^10] = 9
            }
        };
        Console.WriteLine(string.Join(" ", countdown.buffer));
    }
}
