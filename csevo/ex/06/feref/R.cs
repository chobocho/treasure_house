// 슬라이드 p6-v5-fe-later — ref 반복 변수는 포착할 수 없다, C# 7.3
using System;

class App
{
    static void Main()
    {
        int[] nums = { 1, 2, 3 };
        foreach (ref int r in nums.AsSpan())
        {
            Func<int> f = () => r;
        }
    }
}
