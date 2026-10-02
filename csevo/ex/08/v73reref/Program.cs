// 슬라이드 p8-v7_3-refreassign — ref 재할당, C# 7.3
using System;

class App
{
    static void Main()
    {
        int[] arr = { 5, 3, 8, 1 };
        ref int max = ref arr[0];
        for (int i = 1; i < arr.Length; i++)
        {
            if (arr[i] > max) max = ref arr[i];   // rebind the alias
        }
        max = 0;                                  // writes arr[2]
        Console.WriteLine(string.Join(",", arr));
    }

#if BAD
    static ref int Leak(ref int outer)
    {
        int local = 1;
        ref int r = ref outer;
        r = ref local;          // narrower than r
        return ref r;
    }
#endif
}
