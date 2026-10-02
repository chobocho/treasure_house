// 슬라이드 p7-v6-us-ext — 확장 메서드는 확장 호출로만, C# 6.0
using System;
using System.Collections.Generic;
using static System.Linq.Enumerable;

class Program
{
    static void Main()
    {
        IEnumerable<int> nums = Range(1, 5);        // plain static
        IEnumerable<int> odd = nums.Where(n => n % 2 == 1);
        Console.WriteLine(odd.Sum());
#if BAD
        IEnumerable<int> even = Where(nums, n => n % 2 == 0);
#endif
    }
}
