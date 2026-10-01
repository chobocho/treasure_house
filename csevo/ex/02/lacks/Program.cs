// 슬라이드 p2-v1-lacks — C# 1 에 없던 것, C# 1.0
using System;
using System.Collections;

class App
{
    delegate int Op(int x);

    static void Main()
    {
        ArrayList nums = new ArrayList();
        nums.Add(21);
        var n = (int)nums[0];                   // C# 3
        Op twice = x => x * 2;                  // C# 3
        Console.WriteLine($"twice: {twice(n)}"); // C# 6
        int? none = null;                       // C# 2
        Console.WriteLine(none == null);
    }
}
