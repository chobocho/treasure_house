// 슬라이드 p9-v8-staticlocal — static 지역 함수가 쓸 수 있는 것, C# 8.0
using System;

class Order
{
    const int TaxPercent = 10;
    static int fee = 1;
    int qty = 3;

    public int Total(int price)
    {
        int discount = 2;
        return Calc(price) * qty - discount;

        static int Calc(int p)
        {
#if BAD
            p += qty;                      // an instance field: this
            p -= discount;                 // a local of Total
#endif
            Console.WriteLine("Calc may name " + nameof(discount));
            return p * (100 + TaxPercent) / 100 + fee;  // const, static
        }
    }
}

class App
{
    static void Main() => Console.WriteLine(new Order().Total(20));
}
