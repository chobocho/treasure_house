// 슬라이드 p8-v7-ref-init — ref 지역 변수는 변수로만 초기화한다, C# 7.0
using System.Linq;

class App
{
    static int Count() { return 3; }

    static void Main()
    {
        int[] arr = { 1, 2, 3 };
        ref int a;                       // no initializer
        ref int b = arr[0];              // missing 'ref' on the right
        ref int c = ref Count();         // a value, not a variable
        ref int d = ref arr.Count();     // the whats-new example
        ref int e = ref 5;               // a literal
    }
}
